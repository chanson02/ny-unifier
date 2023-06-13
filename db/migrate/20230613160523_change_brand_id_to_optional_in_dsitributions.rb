class ChangeBrandIdToOptionalInDsitributions < ActiveRecord::Migration[7.0]
  def change
    change_column_null :distributions, :brand_id, true
  end
end
