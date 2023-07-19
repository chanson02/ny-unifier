# frozen_string_literal: true

# Same as RowParser, but reuse retailer if none
class ReuseRetailerParser < BaseParser
  def execute
    return unless @report.blob

    rows = @report.csv_rows(@report.blob)[@report.head_row + 1..]
    last_known_retailer = nil

    rows.each do |row|
      next unless parse_row?(row)

      account = account_from_row(row)
      adr = address_from_row(row)
      addressor = NYAddressor.new(adr)
      retailer = account.nil? ? last_known_retailer : find_or_create_retailer(account, addressor)
      last_known_retailer = retailer if retailer

      add_address_to_retailer(row, retailer, addressor)
      brands = brands_from_row(row)
      brands.each do |brand|
        unless brand.nil?
          brand = Brand.find_or_create_by(name: brand)
          brand.save
        end
        distribute(retailer, brand, adr, account, brands_from_row(row))
      end
    end
    @report.parsed = true
    @report.save
  end
end
