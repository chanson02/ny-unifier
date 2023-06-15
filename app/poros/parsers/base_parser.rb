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

  def find_or_create_retailer(name, addressor)
    #addressor = NYAddressor.new(address)
    retailer = Retailer.find_by(adr_hash: addressor.hash) if addressor.hash
    retailer ||= Retailer.find_by(slug: name.parameterize) if name&.parameterize
    return retailer if retailer

    return unless name&.parameterize

    retailer = Retailer.new(name: name, slug: name.parameterize, adr_hash: addressor.hash)
    retailer.save
    retailer
  end

  def add_address_to_retailer(row, retailer, addressor)
    return if retailer.known?

    parts = @instruction.address
    retailer.street = row[parts[0]] if parts[0] && retailer.street.nil?
    retailer.unit = row[parts[1]] if parts[1] && retailer.unit.nil?
    retailer.city = row[parts[2]] if parts[2] && retailer.city.nil?
    retailer.state = row[parts[3]] if parts[3] && retailer.state.nil?
    retailer.postal = row[parts[4]] if parts[4] && retailer.postlal.nil?

    snum = addressor&.parts&.fetch(:street_number)
    snam = addressor&.parts&.fetch(:street_name)
    slab = addressor&.parts&.fetch(:street_label)
    sdir = addressor&.parts&.fetch(:street_direction)
    street = snum || ''
    street += " #{snam}" if snam
    street += " #{slab}" if slab
    street += " #{sdir}" if sdir
    street = nil if street.empty?

    retailer.street = street if street && retailer.street.nil?
    retailer.unit = addressor&.parts&.fetch(:unit) unless retailer.unit
    retailer.city = addressor&.parts&.fetch(:city) unless retailer.city
    retailer.state = addressor&.parts&.fetch(:state) unless retailer.state
    retailer.postal = addressor&.parts&.fetch(:postal) unless retailer.postal

    retailer.save
    retailer
  end

  def brands_from_row(row)
    return unless @instruction.brand

    @instruction.brand = [@instruction.brand] unless @instruction.brand.is_a?(Array)
    result = []
    @instruction.brand.each do |i|
      result << row[i]&.split(',')
    end
    result.flatten(&:strip)
  end
end
