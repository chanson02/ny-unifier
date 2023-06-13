# frozen_string_literal: true

# Standard parser where each row contains all the needed info
class RowParser < BaseParser
  def execute
    # Download the file
    return unless @report.blob
    rows = @report.csv_rows(@report.blob)[@report.head_row + 1..]

    rows.each do |row|
      # start with address, the hash may lead us to a retailer
      # Then look for the retailer name
      account = row[@instruction.retailer]
      adr = address_from_row(row)
      retailer = find_or_create_retailer(account, adr)


      # Then brand
      brands = [nil]

      brands.each do |brand|
        # Create the distribution
        d = Distribution.new(report_id: @report.id, retailer_id: retailer.id)
        d.brand_id = brand.id if brand&.id
        d.save
      end
    end
    @report.parsed = true
    @report.save
  end
end
