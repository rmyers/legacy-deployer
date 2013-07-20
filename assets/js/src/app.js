'use strict';


// Declare app level module which depends on filters, and services
var myApp = angular.module('myApp', ['myApp.filters', 'myApp.services', 'myApp.directives', 'ngCookies','http-auth-interceptor']);

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
    .when('/project/:projectId', {
      templateUrl: '/static/partials/project.html',
      conroller: ProjectController
    })
    .when('/people', {
      templateUrl: '/static/partials/people.html',
      controller: PeopleController
    })
    .when('/', {
      templateUrl: '/static/partials/index.html',
      controller: IndexController
    })
    .otherwise({
      redirectTo: '/'
    });
}]);

// Turn on html5 mode
myApp.config(['$locationProvider', function($locationProvider){
    $locationProvider.html5Mode(true).hashPrefix('!');
}]);