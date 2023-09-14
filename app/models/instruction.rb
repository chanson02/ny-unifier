class Instruction < ApplicationRecord
  has_many :header
  enum structure: {
    row: 'row',
    reuse_retailer: 'row (reuse retailer if none)',
    header_brand: 'row (brand in header)'
  }
  serialize :brand, Array
  serialize :address, Array

  def self.from_params(params)
    params = params[:instruction].transform_values { |v| v.blank? ? nil : v }
    address = [params[:street1], params[:street2], params[:city], params[:state], params[:postal]].map { |v| v&.to_i }
    brands = params[:brand].split(',').map(&:to_i)

    ins = Instruction.find_or_create_by(
      structure: params[:structure],
      retailer: params[:retailer],
      brand: brands,
      address: address,
      phone: params[:phone],
      website: params[:website],
      premise: params[:premise],
      chain: params[:chain],
      condition: params[:condition]
    )
    ins
  end
end
