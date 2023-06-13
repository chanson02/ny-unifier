class ReportsController < ApplicationController
  def index
    @reports = Report.all
  end

  def new
    @report = Report.new
  end

  def create
    upload = params[:report][:file]
    @report = Report.new
    @report.name = upload.original_filename
    @report.files.attach(upload)

    if @report.save
      redirect_to reports_path, notice: "Uploaded #{@report.name}"
    else
      render :new
    end
  end

  def show
    @report = Report.find(params[:id])
    @known = @report.retailers.select(&:known?)
    @unknown = @report.retailers.select(&:unknown?)
  end

  def unifier_report
    report = Report.find(params[:id])
    data = CSV.generate do |csv|
      csv << %w[this is a test]
    end
    send_data data, filename: "#{report.name}_unifier_report.csv", type: 'text/csv'
  end

  private

  def report_params
    params.require(:report).permit(:file)
  end
end
