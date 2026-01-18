from rest_framework.permissions import BasePermission


class IsAdminRole(BasePermission):
    """
    Admin 역할만 접근 가능
    - 전체 시스템 관리 권한
    - Django Admin 접근 가능
    """
    message = "관리자만 접근할 수 있습니다."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_admin_role
        )


class IsStaffRole(BasePermission):
    """
    Staff 역할 이상 접근 가능 (Admin, Staff)
    - 콘텐츠 관리 (단어, 문장, 학습자료)
    - 사용자 지원 (조회)
    """
    message = "스태프 이상의 권한이 필요합니다."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ['admin', 'staff']
        )


class IsUserRole(BasePermission):
    """
    인증된 사용자면 접근 가능 (Admin, Staff, User)
    - 학습 기능 사용
    - 자신의 프로필 관리
    """
    message = "로그인이 필요합니다."

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class IsOwnerOrStaff(BasePermission):
    """
    본인이거나 Staff 이상만 접근 가능
    - 사용자 데이터 조회/수정에 사용
    """
    message = "본인이거나 스태프 권한이 필요합니다."

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        # Staff 이상은 모든 객체 접근 가능
        if request.user.role in ['admin', 'staff']:
            return True

        # 본인 확인 (obj가 User인 경우)
        if hasattr(obj, 'email'):
            return obj == request.user

        # obj가 user 필드를 가진 경우 (예: UserProfile, Progress)
        if hasattr(obj, 'user'):
            return obj.user == request.user

        return False


class IsAdminOrReadOnly(BasePermission):
    """
    Admin은 모든 작업, 나머지는 읽기만 가능
    """
    message = "수정 권한이 없습니다."

    def has_permission(self, request, view):
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_admin_role
        )


class IsStaffOrReadOnly(BasePermission):
    """
    Staff 이상은 모든 작업, 일반 사용자는 읽기만 가능
    - 콘텐츠 API에 사용 (단어, 문장 등)
    """
    message = "수정 권한이 없습니다."

    def has_permission(self, request, view):
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return request.user and request.user.is_authenticated
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ['admin', 'staff']
        )
