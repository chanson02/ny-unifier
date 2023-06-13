# frozen_string_literal: true

# Distribution model
class Distribution < ApplicationRecord
  belongs_to :report
  belongs_to :retailer
  belongs_to :brand, optional: true
end
