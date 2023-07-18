# frozen_string_literal: true

# Containers controller
class ContainersController < ApplicationController
  def index
    @containers = Container.all
  end

  def show
    @container = Container.find(params[:id])
  end

  def new
    @container = Container.new
  end

  def create
    @container = Container.new(allowed_params)
    @container.save ? redirect_to(containers_path) : render(:new)
  end

  def update
    @container = Container.find(params[:id])
    render :show
  end

  def parse
    @container = Container.find(params[:id])
    @container.reports.map(&:parse)
    render json: { status: 'ok' }
  end

  def unifier_report
    container = Container.find(params[:id])
    data = CSV.generate do |csv|
      csv << %w[Source Account\ ID Account\ Name Street Unit City State Postal Brand Phone Website Premise RAW]
      container.reports.each do |report|
        report.distributions.each do |dist|
          retailer = Retailer.find(dist.retailer_id)
          csv << [
            report.name,
            dist.retailer_id,
            retailer.name,
            retailer.street,
            retailer.unit,
            retailer.city,
            retailer.state,
            retailer.postal,
            dist.brands,
            'Not yet implemented',
            'Not yet implemented',
            'Not yet implemented',
            dist.address
          ]
        end
      end
    end
    send_data data, filename: "#{container.name}_unifier_report.csv", type: 'text/csv'
  end

  private

  def allowed_params
    params.require(:container).permit(:name, :date)
  end
end
