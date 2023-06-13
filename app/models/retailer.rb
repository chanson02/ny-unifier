# frozen_string_literal: true

# Retailer model
class Retailer < ApplicationRecord
  before_save :generate_slug

  def known?
    street && city && state && postal
  end

  def unknown?
    !known?
  end

  def generate_slug
    self.slug = name.parameterize
  end

  # for regenerating the hash
  def regen
    return unless street

    full_address = street
    full_address += ", #{unit}" if unit
    full_address += ", #{city}" if city
    full_address += " #{state}" if state
    full_address += ", #{postal}" if postal

    self.adr_hash = NYAddressor.new(full_address).hash
  end
end
