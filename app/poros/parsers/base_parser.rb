# frozen_string_literal: true

# abstract parser
class BaseParser
  def initialize(report)
    @report = report
    @instruction = report.header.instruction
    raise NotImplementedError if self.class.instance_of?(BaseParser)
  end

  def execute
    raise NotImplementedError
  end

  def parse_row?(row)
    return true unless @instruction.condition

    # TODO: Make this a sandbox'd environment

    head = @report.raw_head
    date = @report.container.date
    begin
      return eval(@instruction.condition)
    rescue StandardError => e
      puts "some sort of error message here #{e}"
    end
    false
  end

  def account_from_row(row)
    return row[@instruction.retailer] unless @instruction.address.include?(@instruction.retailer)

    row[@instruction.retailer].split(',')[0]
  end

  # full address as string
  def address_from_row(row)
    parts = @instruction.address
    mask = parts.compact
    return if mask.empty?

    row = row.split(',')[1].strip if parts[0] == @instruction.retailer

    # no street address, probably state and city
    return mask.map { |i| row[i] }.compact.join(', ') if parts[0].nil?

    full_address = row[parts[0]]&.strip || ''
    full_address += " #{row[parts[1]]&.strip}" if parts[1] && row[parts[1]]
    full_address += ", #{row[parts[2]]&.strip}" if parts[2] && row[parts[2]]
    full_address += " #{row[parts[3]]&.strip}" if parts[3] && row[parts[3]]
    full_address += ", #{row[parts[4]]&.strip}" if parts[4] && row[parts[4]]
    full_address
  end

  def find_or_create_chain(retailer)
    return retailer.chain if retailer.chain

    chain = Chain.new(name: retailer.name)
    chain.save

    retailer.chain_id = chain.id
    retailer.save
    chain
  end

  def find_or_create_retailer(name, addressor)
    return unless name&.parameterize || addressor&.hash

    retailer = Retailer.find_or_initialize_by(slug: name.parameterize)
    if retailer.persisted?
      return retailer if retailer.adr_hash && addressor&.hash && retailer.adr_hash == addressor&.hash

      chain = find_or_create_chain(retailer)
      retailer = Retailer.new(slug: name.parameterize, chain_id: chain.id)
    end

    retailer.assign_attributes(name: name, adr_hash: addressor&.hash)
    retailer.save
    retailer
  end

  def add_address_to_retailer(row, retailer, addressor)
    return if retailer.known?

    parts = @instruction.address
    unless parts.compact.length < 2
      retailer.street = row[parts[0]] if parts[0] && retailer.street.nil?
      retailer.unit = row[parts[1]] if parts[1] && retailer.unit.nil?
      retailer.city = row[parts[2]] if parts[2] && retailer.city.nil?
      retailer.state = row[parts[3]] if parts[3] && retailer.state.nil?
      retailer.postal = row[parts[4]] if parts[4] && retailer.postal.nil?
    end

    unless addressor&.parts
      retailer.save
      return retailer
    end

    parts = addressor.parts
    street = parts[:street_number] || ''
    street += " #{parts[:street_name]}" if parts[:street_name]
    street += " #{parts[:street_label]}" if parts[:street_label]
    street += " #{parts[:street_direction]}" if parts[:street_direction]
    street = nil if street.empty?

    retailer.street = street if street && retailer.street.nil?
    retailer.unit = parts[:unit] unless retailer.unit || parts[:unit].nil?
    retailer.city = parts[:city] unless retailer.city || parts[:city].nil?
    retailer.state = parts[:state] unless retailer.state || parts[:state].nil?
    retailer.postal = parts[:postal] unless retailer.postal || parts[:postal].nil?

    retailer.save
    retailer
  end

  def brands_from_row(row)
    return unless @instruction.brand

    @instruction.brand = [@instruction.brand] unless @instruction.brand.is_a?(Array)
    result = []
    @instruction.brand.compact.each do |i|
      result << row[i]&.split(',')
    end
    result.flatten(&:strip)
  end

  def distribute(retailer, brand, raw_address, raw_retailer = nil, raw_brand = nil)
    d = Distribution.new(report_id: @report.id, retailer_id: retailer.id)
    d.brand_id = brand.id if brand&.id
    d.address = raw_address.to_s
    d.brands = raw_brand.to_s
    d.save
    d
  end
end
