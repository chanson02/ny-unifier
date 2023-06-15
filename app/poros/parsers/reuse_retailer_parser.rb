# frozen_string_literal: true

# Same as RowParser, but reuse retailer if none
class ReuseRetailerParser < BaseParser
  def execute
    return unless @report.blob

    rows = @report.csv_rows(@report.blob)[@report.head_row + 1..]
    last_known_retailer = nil

    rows.each do |row|
      next unless parse_row?(row)

      account = row[@instruction.retailer]
      adr = address_from_row(row)
      retailer = account.nil? ? last_known_retailer : find_or_create_retailer(account, adr, row)
      last_known_retailer = retailer if retailer

      brands = brands_from_row(row)
      brands.each do |brand|
        unless brand.nil?
          brand = Brand.find_or_create_by(name: brand)
          brand.save
        end

        d = Distribution.new(report_id: @report.id, retailer_id: retailer.id)
        d.brand_id = brand.id if brand&.id
        d.save
      end
    end
    @report.parsed = true
    @report.save
  end
end
