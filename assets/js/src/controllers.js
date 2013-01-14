'use strict';

/* Controllers */


function MyCtrl1() {}
MyCtrl1.$inject = [];


function MyCtrl2() {
}
MyCtrl2.$inject = [];

function PeopleController($resource, $scope, People) {
    People.query({}, function(data){
        $scope.users = data.objects;
        $scope.count = data.meta.total_count;
    });
};

function LoginController($scope, $http, authService) {
	$scope.submit = function () {
		$http.post('../accounts/login/', 
		    'username='+$scope.username+'&password='+$scope.password).
		    success(function() {
				authService.loginConfirmed();
				$scope.username = '';
				$scope.password = '';
				$scope.error = false;
			}).
			error(function(resp) {
				$scope.error = resp.message;
			});
	};
};

PeopleController.$inject = ['$resource', '$scope', 'People'];
LoginController.$inject = ['$scope', '$http', 'authService']
