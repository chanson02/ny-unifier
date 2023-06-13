# frozen_string_literal: true

# Retailer model
class Retailer < ApplicationRecord
  def known?
    street && city && state && postal
  end

  def unknown?
    !known?
  end

  def update(params)
    puts 'not yet implemented'
  end
end
