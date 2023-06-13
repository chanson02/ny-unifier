# frozen_string_literal: true

Rails.application.routes.draw do
  resources :reports
  get '/reports/:id/unifier-report', to: 'reports#unifier_report', as: 'unifier_report'

  resources :retailers, only: %i[edit update]
  resources :instructions, only: %i[new create]
  root 'reports#index'
end
