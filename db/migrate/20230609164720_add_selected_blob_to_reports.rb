class AddSelectedBlobToReports < ActiveRecord::Migration[7.0]
  def change
    add_column :reports, :selected_blob, :string, null: true
  end
end
