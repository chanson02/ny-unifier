class AddHeadRowToReport < ActiveRecord::Migration[7.0]
  def change
    add_column :reports, :head_row, :integer, null: true
  end
end
