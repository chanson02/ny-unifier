# frozen_string_literal: true

Rails.application.routes.draw do
  resources :reports
  get '/reports/:id/unifier-report', to: 'reports#unifier_report', as: 'unifier_report'
  get '/reports/:id/head', to: 'reports#select_head', as: 'select_head'
  patch '/reports/:id/head', to: 'reports#save_head', as: 'save_head'
  get '/reports/:id/parse', to: 'reports#parse', as: 'parse_report'
  get '/reports/:id/partial-rows', to: 'reports#partial_rows', as: 'partial_rows'

  resources :retailers, only: %i[edit update]

  resources :instructions, only: %i[new create]
  get 'instructions/new/:report_id', to: 'instructions#new', as: 'new_report_instruction'

  resources :containers
  get 'containers/:id/parse', to: 'containers#parse', as: 'parse_container'
  root 'containers#index'
end
