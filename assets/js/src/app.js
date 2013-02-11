'use strict';


// Declare app level module which depends on filters, and services
var myApp = angular.module('myApp', ['myApp.filters', 'myApp.services', 'myApp.directives', 'ngCookies','http-auth-interceptor']).
  config(['$routeProvider', function($routeProvider) {
    $routeProvider.when('/view1', {templateUrl: '/static/partials/partial1.html', controller: MyCtrl1});
    $routeProvider.when('/view2', {templateUrl: '/static/partials/partial2.html', controller: MyCtrl2});
    $routeProvider.when('/people', {templateUrl: '/static/partials/people.html', controller: PeopleController});
    $routeProvider.otherwise({redirectTo: '/view1'});
  }]);

// Turn on html5 mode
myApp.config(['$locationProvider', function($locationProvider){
    $locationProvider.html5Mode(true).hashPrefix('!');	
}]);

// Make a reference to httpProvider for use later
myApp.config(['$httpProvider', function($httpProvider) {
  myApp.$httpProvider = $httpProvider;
}]);

// Add a default header for the Django csrftoken
myApp.run(['$cookies', function($cookies){
  myApp.$httpProvider.defaults.headers.post['X-CSRFToken'] = $cookies['csrftoken'];
}]);
