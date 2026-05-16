import qualified Data.Set as Set

main :: IO ()
main = print answer

rows :: [[Integer]]
rows = take 51 (iterate nextRow [1])
  where
    nextRow xs = zipWith (+) (0 : xs) (xs ++ [0])

isSquarefree :: Integer -> Bool
isSquarefree n = all (\p -> n `mod` (p * p) /= 0) primes
  where
    primes = takeWhile (\p -> p * p <= n) [2,3..]

answer :: Integer
answer =
  sum
    [ n
    | n <- Set.toList (Set.fromList (concat rows))
    , isSquarefree n
    ]
