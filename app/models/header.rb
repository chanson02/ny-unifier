class Header < ApplicationRecord
  belongs_to :instruction
  has_many :reports
end
