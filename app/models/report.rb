# frozen_string_literal: true

# Report
class Report < ApplicationRecord
  belongs_to :header, optional: true
  has_many_attached :file
  attr_reader :file_types

  after_commit :xl_to_csv, on: :create

  @@file_types = [
    'text/csv',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
  ]

  def parse
    return unless file.attached? && file.blob.present?

    fname = ActiveStorage::Filename.new(file.blob.filename.to_s).sanitized
    path = Rails.root.join('tmp', fname)
    File.open(path.to_s, 'wb') do |tf|
      tf.write(file.download)
    end

    set_head
  end


  def xl_to_csv
    return unless file.attached? & file.blobs.present?

    file.blobs.each do |blob|
      type = blob.content_type
      next unless @@file_types[1..2].include? type

      # download blob
      fname = ActiveStorage::Filename.new(blob.filename.to_s).sanitized
      path = Rails.root.join('tmp', fname).to_s
      debugger
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

        file.attach(new_blob)
      end

      File.delete(path) # cleanup
      blob.purge
    end
  end

  private

  def set_head
    return unless header.nil?
  end

  def parse_excel(path)
    xl = Roo::Excelx.new(path)
  end

  def parse_csv(path)
    #CSV.foreach(path, headers:true) do |row|
  end
end
