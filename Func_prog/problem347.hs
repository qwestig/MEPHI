import Control.Monad (forM_, when)
import Data.Array.ST (STUArray, newArray, readArray, runSTUArray, writeArray)
import Data.Array.Unboxed ((!))
import Control.Monad.ST (ST)

main :: IO ()
main = print answer

limit :: Int
limit = 10000000

primeTable :: Int -> ST s (STUArray s Int Bool)
primeTable upper = do
  table <- newArray (0, upper) True
  writeArray table 0 False
  writeArray table 1 False
  forM_ [2..floor (sqrt (fromIntegral upper :: Double))] $ \p -> do
    prime <- readArray table p
    when prime $
      forM_ [p * p, p * p + p..upper] $ \multiple ->
        writeArray table multiple False
  return table

primes :: [Int]
primes = [n | n <- [2..limit `div` 2], primeFlags ! n]
  where
    primeFlags = runSTUArray (primeTable (limit `div` 2))

valuesFor :: Int -> Int -> [Int]
valuesFor p q =
  [ pPower * qPower
  | pPower <- takeWhile (<= limit) (iterate (* p) p)
  , qPower <- takeWhile (<= limit `div` pPower) (iterate (* q) q)
  ]

answer :: Integer
answer =
  fromIntegral
    (sum
    [ maximum (valuesFor p q)
    | p <- takeWhile (\x -> x * 2 <= limit) primes
    , q <- takeWhile (\x -> p * x <= limit) primes
    , p < q
    ])
