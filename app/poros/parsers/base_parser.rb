# frozen_string_literal: true

# abstract parser
class BaseParser
  def initialize(report)
    @report = report
    @instruction = report.header.instruction
    raise NotImplementedError if self.class.instance_of?(BaseParser)
  end

  # full address as string
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

  def find_or_create_retailer(name, address, row=nil)
    addressor = NYAddressor.new(address)
    retailer = Retailer.find_by(adr_hash: addressor.hash) if addressor.hash
    retailer ||= Retailer.find_by(slug: name.parameterize)
    return retailer if retailer

    retailer = Retailer.new(name: name, slug: name.parameterize, adr_hash: addressor.hash)
    retailer.save
    retailer
    # TODO: use the row data to set street, city, state, postal
  end

end
