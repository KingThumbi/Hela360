import { useCurrentSession } from "./useCurrentSession";

export function useCurrentUser() {
  const query = useCurrentSession();

  return {
    ...query,
    data: query.data?.identity,
  };
}

export default useCurrentUser;
