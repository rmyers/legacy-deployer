'use strict';

/* Controllers */

function MainCntl($scope, $route, $routeParams, $location) {
  $scope.$route = $route;
  $scope.$location = $location;
  $scope.$routeParams = $routeParams;
  console.log($scope.user);
};

function DashboardController() {}


function SignupController($scope, $http, authService) {
  $scope.page = 'signup';
  $scope.submit = function () {
  	if ($scope.password != $scope.confirm) {
  	  $scope.error = "Passwords do not match!";
  	} else {
		$http.post('/accounts/signup/', jQuery.param($scope.user), {
			headers: {'Content-Type': 'application/x-www-form-urlencoded'}
		  }).
	      success(function() {
			authService.loginConfirmed();
			$scope.username = '';
			$scope.password = '';
			$scope.error = false;
		  }).
		  error(function(resp) {
		  	console.log(resp.message);
			$scope.error = resp.message;
		  });
	    };
  	}
};

function PeopleController($resource, $scope, People) {
    People.query({}, function(data){
        $scope.users = data.objects;
        $scope.count = data.meta.total_count;
    });
};

function LoginController($scope, $http, authService, $location) {
	$scope.page = 'signup';
	$scope.submit = function () {
		$http.post('/accounts/signin/', jQuery.param($scope.user), {
			headers: {'Content-Type': 'application/x-www-form-urlencoded'}
		  }).
		  success(function(resp) {
		  	console.log(resp);
			authService.loginConfirmed();
			$scope.error = false;
			$scope.user = resp;
			$location.url('/dashboard');
		  }).
		  error(function(resp) {
			$scope.error = resp.message;
		  });
	};
};

MainCntl.$inject = ['$scope', '$route', '$routeParams', '$location'];
DashboardController.$inject = [];
LoginController.$inject = ['$scope', '$http', 'authService', '$location'];
PeopleController.$inject = ['$resource', '$scope', 'People'];
SignupController.$inject = ['$scope', '$http', 'authService'];
