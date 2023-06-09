class Report < ApplicationRecord
  belongs_to :header, optional: true
  has_one_attached :file

  def parse
    return unless file.attached? && file.blob.present?

    fname = ActiveStorage::Filename.new(file.blob.filename.to_s).sanitized
    type = file.blob.content_type
    path = Rails.root.join('tmp', fname)
    File.open(path.to_s, 'wb') do |tf|
      tf.write(file.download)
    end

    if ['application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'].include?(type)
      parse_excel(path)
    elsif ['text/csv'].include?(type)
      parse_csv(path)
    else
      puts 'Unable to process type', type
    end

    File.delete(path) # clean up
  end

  private

  def parse_excel(path)
    xl = Roo::Excelx.new(path)
  end

  def parse_csv(path)
    #CSV.foreach(path, headers:true) do |row|
  end
end
