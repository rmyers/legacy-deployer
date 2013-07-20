'use strict';

/* Services */


// Demonstrate how to register services
// In this case it is a simple value service.
angular.module('myApp.services', ['ngResource']).
  factory('People', function($resource) {
      return $resource('../api/v1/user/:userId', {}, {
        query: {method:'GET', params: {limit: 10}}, isArray:false
      });
  }).
  factory('Group', function($resource) {
  	return $resource('/api/v1/group/:groupId', {}, {
        query: {method:'GET', params: {limit: 100}}, isArray:false
      });
  }).
  factory('Event', function($resource) {
  	return $resource('/api/v1/group/:groupId/event/:eventId', {}, {
        query: {method:'GET', params: {limit: 100}}, isArray:false
      });
  }).
  factory('Project', function($resource) {
  	return $resource('/api/v1/project/:projectId', {}, {
        query: {method:'GET', params: {limit: 100}}, isArray:false
      });
  }).
  factory('User', function() {
  	return {user_id: 0, name: null}
  });
