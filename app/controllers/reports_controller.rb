class ReportsController < ApplicationController
  def index
    @reports = Report.all
  end

  def create
    upload = params[:report][:file]
    @report = Report.new
    @report.container_id = params[:report][:container_id]
    @report.name = upload.original_filename
    @report.files.attach(upload)

    if @report.save
      render json: { status: 'ok' }
      @report.xl_to_csv
      @report.find_head
    else
      render json: @report.errors, status: :unprocessable_entity
    end
  end

  def show
    @report = Report.find(params[:id])
    @known = @report.retailers.select(&:known?).uniq
    @unknown = @report.retailers.select(&:unknown?).uniq
  end

  def unifier_report
    report = Report.find(params[:id])
    data = CSV.generate do |csv|
      csv << %w[this is a test]
    end
    send_data data, filename: "#{report.name}_unifier_report.csv", type: 'text/csv'
  end

  def select_head
    @report = Report.find(params[:id])
    render 'select_head'
  end

  def save_head
    @report = Report.find(params[:id])
    @report.update(selected_blob: params[:report][:selected_blob], head_row: params[:report][:head_row])
    @report.save ? redirect_to(report_path(@report)) : render('select_head')
    @report.set_head(@report.blob, @report.head_row)
  end

  def parse
    @report = Report.find(params[:id])
    # delete the old parsing
    Rails.env.production? ? ParseReportJob.perform_later(@report.id) : @report.parse
    render json: { status: 'ok' }
  end

  private

  def report_params
    params.require(:report).permit(:file)
  end
end
