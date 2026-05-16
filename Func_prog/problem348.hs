import qualified Data.Map.Strict as Map

main :: IO ()
main = print answer

limit :: Integer
limit = 1000000000

isPalindrome :: Integer -> Bool
isPalindrome n = s == reverse s
  where
    s = show n

representations :: Map.Map Integer Int
representations =
  Map.fromListWith (+)
    [ (square + cube, 1)
    | square <- takeWhile (< limit) [n * n | n <- [1..]]
    , cube <- takeWhile (< limit - square) [n * n * n | n <- [1..]]
    ]

answer :: Integer
answer =
  sum
    (take 5
      [ n
      | (n, count) <- Map.toAscList representations
      , count == 4
      , isPalindrome n
      ])
