import Data.List (sort)

main :: IO ()
main = print answer

digitSum :: Integer -> Integer
digitSum = sum . map (read . (:[])) . show

validNumbers :: [Integer]
validNumbers =
  sort
    [ value
    | base <- [2..100]
    , exponent <- [2..15]
    , let value = base ^ exponent
    , digitSum value == base
    ]

answer :: Integer
answer = validNumbers !! 29
