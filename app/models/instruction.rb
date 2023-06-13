class Instruction < ApplicationRecord
  has_many :header
  enum structure: {
    row: 'row'
  }
  serialize :brand, Array
  serialize :address, Array

  def self.from_params(params)
    params = params[:instruction].transform_values { |v| v.blank? ? nil : v }
    address = [params[:street1], params[:street2], params[:city], params[:state], params[:postal]]
    ins = Instruction.new(
      structure: params[:structure],
      retailer: params[:retailer],
      brand: [params[:brand]],
      address: address,
      phone: params[:phone],
      website: params[:website],
      premise: params[:premise],
      chain: params[:chain],
      condition: params[:condition]
    )
    return ins
  end
end
