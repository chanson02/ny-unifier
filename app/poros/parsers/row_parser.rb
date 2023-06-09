# frozen_string_literal: true

# Standard parser where each row contains all the needed info
class RowParser < BaseParser
  def execute
    # Download the file
    return unless @report.blob
    rows = @report.csv_rows(@report.blob)

    debugger
    rows.each do |row|
      # start with address, the hash may lead us to a retailer
      # next go to retailer
      # Then brand
    end
    # Create Retailers, Brands?, and Distributions
  end
end
