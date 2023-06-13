class AddRawHeadToReports < ActiveRecord::Migration[7.0]
  def change
    add_column :reports, :raw_head, :text, null: true
  end
end
