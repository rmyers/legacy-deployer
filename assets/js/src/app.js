'use strict';


// Declare app level module which depends on filters, and services
var myApp = angular.module('myApp', ['myApp.filters', 'myApp.services', 'myApp.directives', 'ngCookies','http-auth-interceptor']).
  config(['$routeProvider', function($routeProvider) {
    $routeProvider.when('/dashboard', {templateUrl: '/static/partials/partial1.html', controller: MyCtrl1});
    $routeProvider.when('/signup', {templateUrl: '/static/partials/signup.html', controller: SignupController});
    $routeProvider.when('/people', {templateUrl: '/static/partials/people.html', controller: PeopleController});
    $routeProvider.otherwise({redirectTo: '/dashboard'});
  }]);

// Turn on html5 mode
myApp.config(['$locationProvider', function($locationProvider){
    $locationProvider.html5Mode(true).hashPrefix('!');	
}]);