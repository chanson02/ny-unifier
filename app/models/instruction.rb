class Instruction < ApplicationRecord
  has_many :header
  enum structure: {
    row: 'row'
  }
  serialize :brand, Array
  serialize :address, Array
end
