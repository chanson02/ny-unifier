# frozen_string_literal: true

# This parser is used when brand names are in the header
class HeaderBrandParser < BaseParser
  def parse_col?(row, col)
    return true unless @instruction.condition

    head = @report.raw_head
    date = @report.container.date

    begin
      return eval(@instruction.condition)
    rescue StandardError => e
      puts "some sort of error message here #{e}"
    end
    false
  end

  def brands_from_row(row)
    return unless @instruction.brand

    result = []
    @instruction.brand.compact.each do |col|
      result << @report.raw_head[col] if parse_col?(row, col)
    end
    result.flatten(&:strip)
  end

  def execute
    return unless @report.blob

    rows = @report.csv_rows(@report.blob)[@report.head_row + 1..]
    rows.each do |row|
      account = account_from_row(row)
      adr = address_from_row(row)
      addressor = NYAddressor.new(adr)
      retailer = find_or_create_retailer(account, addressor)

      add_address_to_retailer(row, retailer, addressor)
      brands = brands_from_row(row)

      if brands.empty?
        distribute(retailer, nil, adr, account)
      else
        brands.each do |brand|
          unless brand.nil?
            b = Brand.find_or_create_by(name: brand)
            b.save
          end
          distribute(retailer, b, adr, account, brand)
        end
      end
    end

    @report.parsed = true
    @report.save
  end
end
