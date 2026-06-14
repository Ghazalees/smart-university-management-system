import { useDispatch, useSelector } from "react-redux";
import {
  logout,
  selectCurrentRole,
  selectCurrentToken,
  selectCurrentUser,
} from "../states/authSlice";

export const useAuth = () => {
  const dispatch = useDispatch();

  const user = useSelector(selectCurrentUser);
  const token = useSelector(selectCurrentToken);
  const role = useSelector(selectCurrentRole);

  return {
    user, // Contains your base user info (e.g. email, names)
    token, // Your active JWT string (accessToken)
    role, // The explicit role string (e.g., 'student', 'staff')
    isAuthenticated: !!token, // Helper boolean
    logout: () => dispatch(logout()), // Clean wrapper to fire the logout action
  };
};
