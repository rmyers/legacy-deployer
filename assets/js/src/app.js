'use strict';


// Declare app level module which depends on filters, and services
var myApp = angular.module('myApp', ['myApp.filters', 'myApp.services', 'myApp.directives', 'ngCookies','http-auth-interceptor'])

// Application routes
myApp.config(['$routeProvider', function($routeProvider) {
  	$routeProvider
      .when('/dashboard', {
      	templateUrl: '/static/partials/dashboard.html', 
      	controller: DashboardController
      })
  	  .when('/signin', {
  	  	templateUrl: '/static/partials/signin.html', 
      	controller: LoginController
  	  })
      .when('/signup', {
      	templateUrl: '/static/partials/signup.html',
      	controller: SignupController
      })
      .when('/people', {
      	templateUrl: '/static/partials/people.html',
      	controller: PeopleController
      })
      .otherwise({
      	redirectTo: '/dashboard'
      });
}]);

// Turn on html5 mode
myApp.config(['$locationProvider', function($locationProvider){
    $locationProvider.html5Mode(true).hashPrefix('!');	
}]);