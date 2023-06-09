class AddHeaderToReports < ActiveRecord::Migration[7.0]
  def change
    add_reference :reports, :header, null: true, foreign_key: true
  end
end
