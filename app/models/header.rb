class Header < ApplicationRecord
  belongs_to :instruction, optional: true
  has_many :reports

  MONTHS = %w[january jan february feb march mar april apr may june jun july jul august aug september sep october oct november nov december dec].freeze

  # this is intended to be a row from a csv
  def self.clean(str)
    # replace all digits with |
    # replace all months with |
    # replace all , with _
    str = str.join('_') if str.is_a?(Array)
    str.to_s.strip.downcase.parameterize.gsub(/\d+/, '|').gsub(/\b(?:#{MONTHS.join('|')})\b/, '|')
  end
end
