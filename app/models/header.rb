class Header < ApplicationRecord
  belongs_to :instruction, optional: true
  has_many :reports

  # this is intended to be a row from a csv
  def self.clean(str)
    str.to_s.strip.downcase.parameterize
  end
end
