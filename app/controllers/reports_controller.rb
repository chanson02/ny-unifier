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

  private

  def report_params
    params.require(:report).permit(:file)
  end
end
