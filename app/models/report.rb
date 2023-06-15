# frozen_string_literal: true

# Report
class Report < ApplicationRecord
  belongs_to :container
  belongs_to :header, optional: true

  has_many :distributions
  has_many :retailers, through: :distributions
  has_many_attached :files

  serialize :raw_head, Array
  attr_reader :file_types

  @@file_types = [
    'text/csv',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
  ]

  def parse
    return unless files.attached? && files.blobs.present?
    return unless blob && header&.instruction

    parser = find_parser
    return unless parser

    parser.new(self).execute
  end

  def blob
    return files.blobs.find_by(key: selected_blob) if selected_blob.present?
    return files.blobs.first if files.blobs.length == 1
  end

  def xl_to_csv
    return unless files.attached? & files.blobs.present?

    files.blobs.each do |blob|
      type = blob.content_type
      next unless @@file_types[1..2].include? type

      # download blob
      fname = ActiveStorage::Filename.new(blob.filename.to_s).sanitized
      path = Rails.root.join('tmp', fname).to_s
      File.open(path, 'wb') do |tf|
        tf.write(blob.download)
      end

      # convert to csv
      wb = Roo::Spreadsheet.open(path)
      wb.sheets.each do |sheet|
        new_name = "#{fname.rpartition('.').first}###{sheet}"
        csv = wb.sheet(sheet).to_csv

        new_blob = ActiveStorage::Blob.create_and_upload!(
          io: StringIO.new(csv),
          filename: new_name,
          content_type: 'text/csv'
        )

        files.attach(new_blob)
      end

      File.delete(path) # cleanup
      blob.attachments.first.purge #.purge_all?
      blob.purge
    end
    save
  end

  def find_head
    # is there a selected_blob? if not go through all files
    blobs = (selected_blob.nil? ? files.blobs : [blob])

    # check if user set a specific start row
    if head_row && (blobs.length == 1 || blob)
      b = blob || blobs.first
      set_head(b, head_row)
      return
    end

    # find a row that is similar to one of the `headers`
    blb = nil
    ndx = nil
    hed = nil
    blobs.each do |blob|
      blb = blob
      rows = csv_rows(blob)[..20]
      rows.each_with_index do |row, i|
        ndx = i
        hed = Header.find_by(value: Header.clean(row))
        break if hed
      end
      break if hed
    end
    set_head(blb, ndx) && return if hed

    # make a new header out of the first row
    # set_head(blobs.first, 0)
  end

  def set_head(blob, row)
    # delete old head? If there's no instruction?
    self.head_row = row
    self.raw_head = csv_rows(blob)[row]
    value = Header.clean(raw_head)
    self.header = Header.find_or_create_by(value: value)
    self.selected_blob = blob.key
    save
    header
  end

  def csv_rows(blob, headers: false)
    return unless @@file_types[0] == blob&.content_type

    # download blob
    fname = ActiveStorage::Filename.new(blob.filename.to_s).sanitized
    path = Rails.root.join('tmp', fname).to_s
    File.open(path, 'wb') do |tf|
      tf.write(blob.download)
    end

    result = []
    CSV.foreach(path, headers: headers) do |r|
      result << r
    end

    File.delete(path)
    result
  end

  def find_parser
    ins = header.instruction
    return unless ins&.structure

    case ins.structure
    when 'row'
      RowParser
    when 'reuse_retailer'
      ReuseRetailerParser
    end
  end
end
