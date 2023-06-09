# frozen_string_literal: true

# abstract parser
class BaseParser
  def initialize(report)
    @report = report
    @instruction = report.header.instruction
    raise NotImplementedError if self.class.instance_of?(BaseParser)
  end

  def retailer_from_row(row)
  end

  def address_from_row(row)
    parts = @instruction.address
    mask = parts.compact
    return if mask.empty?

    # no street address, probably state and city
    return mask.map { |i| row[i] }.compact.join(', ') if parts[0].nil?

    full_address = row[parts[0]]
    full_address += " #{row[parts[1]]}" if parts[1]
    full_address += ", #{row[parts[2]]}" if parts[2]
    full_address += " #{row[parts[3]]}" if parts[3]
    full_address += ", #{row[parts[4]]}" if parts[4]
    full_address
  end
end
