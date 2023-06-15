# frozen_string_literal: true

# Standard parser where each row contains all the needed info
class RowParser < BaseParser
  def execute
    # Download the file
    return unless @report.blob
    rows = @report.csv_rows(@report.blob)[@report.head_row + 1..]

    rows.each do |row|
      next unless parse_row?(row)

      # start with address, the hash may lead us to a retailer
      # Then look for the retailer name
      account = row[@instruction.retailer]
      adr = address_from_row(row)
      next if (account.nil? || account&.empty?) && (adr.nil? || adr&.empty?)

      addressor = NYAddressor.new(adr)
      retailer = find_or_create_retailer(account, addressor)
      next unless retailer # something failed

      add_address_to_retailer(row, retailer, addressor)
      brands = brands_from_row(row)
      brands.each do |brand|
        # Create the distribution
        unless brand.nil?
          brand = Brand.find_or_create_by(name: brand)
          brand.save
        end
        distribute(retailer, brand, account, brands_from_row(row))
      end
    end
    @report.parsed = true
    @report.save
  end
end
