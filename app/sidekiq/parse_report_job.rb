class ParseReportJob
  include Sidekiq::Job

  def perform(report_id)
    report = report.find(report_id)
    report.parse
  end
end
