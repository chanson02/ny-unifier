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

      # Create the distribution
    end
  end
end
