import Control.Monad (forM_, when)
import Data.Array.ST (STUArray, newArray, readArray, runSTUArray, writeArray)
import Data.Array.Unboxed ((!))
import Data.Bits (popCount, xor)
import Control.Monad.ST (ST)

main :: IO ()
main = print answer

limit :: Int
limit = 20000000

digitSegments :: [Int]
digitSegments =
  [ 0x77
  , 0x24
  , 0x5D
  , 0x6D
  , 0x2E
  , 0x6B
  , 0x7B
  , 0x27
  , 0x7F
  , 0x6F
  ]

digits :: Int -> [Int]
digits n = map (read . (:[])) (show n)

segmentsOn :: Int -> Int
segmentsOn n = sum [popCount (digitSegments !! d) | d <- digits n]

transition :: Int -> Int -> Int
transition a b = sum [popCount (x `xor` y) | (x, y) <- pairs]
  where
    da = reverse (digits a)
    db = reverse (digits b)
    pairs =
      [ (segmentAt da i, segmentAt db i)
      | i <- [0..max (length da) (length db) - 1]
      ]
    segmentAt ds i
      | i < length ds = digitSegments !! (ds !! i)
      | otherwise = 0

digitalRootChain :: Int -> [Int]
digitalRootChain n
  | n < 10 = [n]
  | otherwise = n : digitalRootChain (sum (digits n))

samCost :: [Int] -> Int
samCost chain = 2 * sum (map segmentsOn chain)

maxCost :: [Int] -> Int
maxCost [] = 0
maxCost chain@(firstNumber:_) =
  segmentsOn firstNumber + sum (zipWith transition chain (drop 1 chain)) + segmentsOn (last chain)

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

primesInRange :: [Int]
primesInRange = [n | n <- [10000000..limit], primeFlags ! n]
  where
    primeFlags = runSTUArray (primeTable limit)

answer :: Int
answer = sum [samCost chain - maxCost chain | prime <- primesInRange, let chain = digitalRootChain prime]
