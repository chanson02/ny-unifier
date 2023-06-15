class Header < ApplicationRecord
  belongs_to :instruction, optional: true
  has_many :reports

  IGNORE_SYMBOL = '#'.freeze
  MONTHS = %w[january jan february feb march mar april apr may june jun july jul august aug september sep october oct november nov december dec].freeze

  # this is intended to be a row from a csv
  def self.clean(str)
    # ignore digits
    # ignore months
    # replace all , with _
    # remove repeating _|'s
    str = str.join('_') if str.is_a?(Array)
    str
      .to_s
      .strip
      .downcase
      .parameterize
      .gsub(/\d+/, IGNORE_SYMBOL)
      .gsub(/\b(?:#{MONTHS.join('|')})\b/, IGNORE_SYMBOL)
  end
end
