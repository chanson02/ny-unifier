class Header < ApplicationRecord
  belongs_to :instruction
  has_many :reports

  # this is intended to be a row from a csv
  def self.clean(str)
    result = str.strip
    result.gsub!(/s+/, ' ')  # remove spaces
    result.gsub!(/\W+/, '_') # _ any weird chars
    result.downcase
  end
end
