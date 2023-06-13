Rails.application.routes.draw do
  resources :reports
  resources :retailers, only: [:edit, :update]
  # root "articles#index"
end
