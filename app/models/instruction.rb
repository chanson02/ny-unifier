class Instruction < ApplicationRecord
  enum structure: {
    row: 'row'
  }
  serialize :brand, Array
  serialize :address, Array
end
